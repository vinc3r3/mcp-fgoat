"""Checks for 07-private-uploads. Each function returns (passed, evidence)."""
from checklib import (URL, api_headers, app_builds, http, migration_in_repo as _in_repo,  # noqa: F401
                      scalar, sign_in, sql, stayed_in_mcp)

GPX = b'<?xml version="1.0"?><gpx version="1.1" creator="check"><trk><name>check</name></trk></gpx>'
GPX_TYPE = "application/gpx+xml"
_members = {}
_uploaded = {}


def member(name):
    """(access token, user id) for a seeded member, signed in once per grading run."""
    if name not in _members:
        _members[name] = sign_in(name)
    return _members[name]


def upload(token, path, data=GPX, content_type=GPX_TYPE, method="POST"):
    return http(method, f"{URL}/storage/v1/object/tracks/{path}",
                api_headers(token, {"Content-Type": content_type}), raw=data, timeout=120)


def stored(path):
    return scalar(f"select count(*) from storage.objects where bucket_id = 'tracks' and name = '{path}'")


def alice_file():
    """Alice's uploaded file, created once and shared by the checks that need it."""
    if not _uploaded:
        token, alice = member("alice")
        path = f"{alice}/check-track.gpx"
        status, data = upload(token, path)
        _uploaded.update(path=path, status=status, data=data)
    return _uploaded


def bucket_is_private(ctx):
    got = sql("select public from storage.buckets where id = 'tracks' or name = 'tracks'")
    if not got:
        return False, "no bucket called tracks"
    return got[0]["public"] is False, f"tracks bucket is {'public' if got[0]['public'] else 'private'}"


def member_can_upload(ctx):
    f = alice_file()
    return f["status"] == 200 and stored(f["path"]) == 1, f"Alice's upload -> {f['status']} {str(f['data'])[:100]}"


def other_member_can_download(ctx):
    f = alice_file()
    token, _ = member("bob")
    status, body = http("GET", f"{URL}/storage/v1/object/authenticated/tracks/{f['path']}", api_headers(token))
    return status == 200 and "<gpx" in str(body), f"Bob's download -> {status}"


def visitor_cannot_download(ctx):
    f = alice_file()
    if stored(f["path"]) != 1:
        return False, "no file to test with: Alice's upload did not succeed"
    results = {kind: http("GET", f"{URL}/storage/v1/object/{kind}/tracks/{f['path']}", api_headers())[0]
               for kind in ("public", "authenticated")}
    return all(s >= 400 for s in results.values()), f"visitor download attempts -> {results}"


def cannot_upload_into_another_folder(ctx):
    token, _ = member("bob")
    _, alice = member("alice")
    path = f"{alice}/planted-by-bob.gpx"
    status, _ = upload(token, path)
    if scalar("select count(*) from storage.buckets where id = 'tracks'") == 0:
        return False, "no bucket called tracks"
    return stored(path) == 0, f"Bob's upload into Alice's folder -> {status}; file stored: {bool(stored(path))}"


def only_uploader_can_delete(ctx):
    f = alice_file()
    if stored(f["path"]) != 1:
        return False, "no file to test with: Alice's upload did not succeed"
    bob, _ = member("bob")
    alice, _ = member("alice")
    http("DELETE", f"{URL}/storage/v1/object/tracks/{f['path']}", api_headers(bob))
    after_bob = stored(f["path"])
    http("DELETE", f"{URL}/storage/v1/object/tracks/{f['path']}", api_headers(alice))
    after_alice = stored(f["path"])
    _uploaded.clear()
    return after_bob == 1 and after_alice == 0, (
        f"after Bob's delete the file {'survived' if after_bob else 'was deleted'}; "
        f"after Alice's delete it {'is gone' if not after_alice else 'is still there'}")


def size_limit_enforced(ctx):
    token, alice = member("alice")
    path = f"{alice}/too-big.gpx"
    status, _ = upload(token, path, data=GPX + b" " * (6 * 1024 * 1024))
    if scalar("select count(*) from storage.buckets where id = 'tracks'") == 0:
        return False, "no bucket called tracks"
    return stored(path) == 0, f"6 MB upload -> {status}; file stored: {bool(stored(path))}"


def type_limit_enforced(ctx):
    token, alice = member("alice")
    path = f"{alice}/photo.png"
    status, _ = upload(token, path, data=b"\x89PNG\r\n\x1a\n" + b"0" * 64, content_type="image/png")
    if scalar("select count(*) from storage.buckets where id = 'tracks'") == 0:
        return False, "no bucket called tracks"
    return stored(path) == 0, f"PNG upload -> {status}; file stored: {bool(stored(path))}"


def setup_in_repo(ctx):
    return _in_repo(ctx, "tracks")
