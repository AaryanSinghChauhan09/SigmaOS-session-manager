"""Live session save/restore for SigmaOS-session-manager.

Principles: isolated store model (self_test uses a tempfile directory and
never the real home), fail-fast on unknown or duplicate sessions, dry-run
style restore plan (relaunch steps are planned, not executed), deterministic
listing.
"""
import argparse, json, os, re, sys

ENGINE = {
    "name": "sigma-session",
    "summary": "Start, stop, save and restore live sessions",
    "language": "python",
    "verbs": ["start", "stop", "save", "restore", "list"],
    "principles": ["Fail-Fast", "Pure Plan / Thin Execute",
                   "Deterministic Testing", "KISS", "Information Hiding"],
}

cli_doc = """\
$ sigma-session --store ./sessions start browse --app firefox --app terminal
$ sigma-session --store ./sessions save browse-01
$ sigma-session --store ./sessions stop browse-01
$ sigma-session --store ./sessions restore browse-01
$ sigma-session --store ./sessions list
"""

_NAME_RE = re.compile(r"^[A-Za-z0-9._-]{1,32}$")
_ID_RE = re.compile(r"^[A-Za-z0-9._-]+-\d{2}$")


class SessionError(Exception):
    pass


def _path(store, sid):
    return os.path.join(store, sid + ".json")


def _write(store, session):
    os.makedirs(store, exist_ok=True)
    path = _path(store, session["id"])
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(session, fh, indent=1, sort_keys=True)
    os.replace(tmp, path)
    return session


def _read(store, sid):
    if not _ID_RE.match(str(sid)):
        raise SessionError(f"bad session id: {sid!r}")
    path = _path(store, sid)
    if not os.path.isfile(path):
        raise SessionError(f"no such session: {sid}")
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def start(store, name, apps=()):
    """Create a new running session; ids are unique (name-01, name-02, ...)."""
    if not _NAME_RE.match(name):
        raise SessionError(f"bad session name: {name!r}")
    normalized = _normalize_apps(apps)
    used = {sid.rsplit("-", 1)[-1] for sid in list_ids(store)
            if sid.rsplit("-", 1)[0] == name}
    n = 1
    while f"{n:02d}" in used:
        n += 1
    session = {"id": f"{name}-{n:02d}", "name": name, "state": "running",
               "apps": normalized}
    return _write(store, session)


def _normalize_apps(apps):
    out = []
    for app in apps:
        if isinstance(app, str):
            app = {"cmd": app, "cwd": "/"}
        if not isinstance(app, dict) or not app.get("cmd"):
            raise SessionError(f"bad app spec: {app!r}")
        cwd = app.get("cwd", "/")
        if not isinstance(cwd, str) or not cwd.startswith("/"):
            raise SessionError(f"bad cwd for {app['cmd']!r}: {cwd!r}")
        out.append({"cmd": str(app["cmd"]), "cwd": cwd})
    return out


def stop(store, sid):
    session = _read(store, sid)
    if session["state"] == "stopped":
        raise SessionError(f"session already stopped: {sid}")
    session["state"] = "stopped"
    return _write(store, session)


def save(store, sid, apps=None):
    """Persist the app snapshot of a session (apps replaced if given)."""
    session = _read(store, sid)
    if apps is not None:
        session["apps"] = _normalize_apps(apps)
    session["saved"] = True
    return _write(store, session)


def restore(store, sid):
    """Pure-ish: returns an ordered relaunch plan and marks the session running."""
    session = _read(store, sid)
    if not session.get("saved") and not session.get("apps"):
        raise SessionError(f"nothing to restore for {sid}")
    if not session.get("apps"):
        raise SessionError(f"nothing to restore for {sid}")
    plan = [{"action": "launch", "cmd": a["cmd"], "cwd": a["cwd"]}
            for a in session["apps"]]
    session["state"] = "running"
    _write(store, session)
    return plan


def list_ids(store):
    if not os.path.isdir(store):
        return []
    return sorted(f[:-5] for f in os.listdir(store)
                  if f.endswith(".json") and not f.endswith(".tmp.json"))


def list_sessions(store):
    return [_read(store, sid) for sid in list_ids(store)]


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog=ENGINE["name"], description=ENGINE["summary"])
    p.add_argument("--store", default=os.path.expanduser(
        "~/.local/state/sigmaos/sessions"), help="session store directory")
    sub = p.add_subparsers(dest="cmd", required=True)
    st = sub.add_parser("start", help="create a running session")
    st.add_argument("name")
    st.add_argument("--app", action="append", default=[], dest="apps",
                    metavar="CMD", help="application command (repeatable)")
    sp = sub.add_parser("stop", help="stop a session")
    sp.add_argument("id")
    sv = sub.add_parser("save", help="snapshot a session's app list")
    sv.add_argument("id")
    sv.add_argument("--app", action="append", default=None, dest="apps",
                    metavar="CMD", help="replace the saved app list")
    rs = sub.add_parser("restore", help="relaunch plan for a session")
    rs.add_argument("id")
    sub.add_parser("list", help="list sessions")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.cmd == "start":
            s = start(args.store, args.name, apps=args.apps)
            print(f"{s['id']} ({s['state']}, {len(s['apps'])} app(s))")
        elif args.cmd == "stop":
            s = stop(args.store, args.id)
            print(f"{s['id']} {s['state']}")
        elif args.cmd == "save":
            s = save(args.store, args.id, apps=args.apps)
            print(f"{s['id']} saved ({len(s['apps'])} app(s))")
        elif args.cmd == "restore":
            for step in restore(args.store, args.id):
                print(f"{step['action']} {step['cmd']} (cwd={step['cwd']})")
        elif args.cmd == "list":
            for s in list_sessions(args.store):
                print(f"{s['id']}: {s['state']} apps={len(s['apps'])}")
        return 0
    except (SessionError, OSError, ValueError, json.JSONDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


def self_test() -> None:
    import tempfile
    with tempfile.TemporaryDirectory() as store:
        # start: unique ids, normalized apps
        s1 = start(store, "browse", apps=["firefox", {"cmd": "mpv", "cwd": "/videos"}])
        assert s1["id"] == "browse-01" and s1["state"] == "running"
        assert s1["apps"][0] == {"cmd": "firefox", "cwd": "/"}
        assert s1["apps"][1]["cwd"] == "/videos"
        s2 = start(store, "browse")
        assert s2["id"] == "browse-02"                  # collision-free ids
        # list: deterministic
        assert [s["id"] for s in list_sessions(store)] == ["browse-01", "browse-02"]
        # save / stop / restore lifecycle on s1
        saved = save(store, s1["id"])
        assert saved["saved"] is True and len(saved["apps"]) == 2
        stopped = stop(store, s1["id"])
        assert stopped["state"] == "stopped"
        assert _read(store, s1["id"])["state"] == "stopped"
        plan = restore(store, s1["id"])
        assert [p["cmd"] for p in plan] == ["firefox", "mpv"]   # saved order kept
        assert all(p["action"] == "launch" for p in plan)
        assert _read(store, s1["id"])["state"] == "running"
        # save with a new app list replaces it
        save(store, s2["id"], apps=["only-one"])
        assert len(_read(store, s2["id"])["apps"]) == 1
        # restore of a session with no apps at all
        s3 = start(store, "empty")
        try:
            restore(store, s3["id"])
        except SessionError as e:
            assert "nothing to restore" in str(e)
        else:
            raise AssertionError("empty restore not rejected")
        # fail-fast: stop -> stopped, second stop rejected
        stopped_again = stop(store, s1["id"])
        assert stopped_again["state"] == "stopped"
        try:
            stop(store, s1["id"])
        except SessionError as e:
            assert "already stopped" in str(e)
        else:
            raise AssertionError("double stop not rejected")
        for bad_call in (
            lambda: start(store, "bad name"),
            lambda: start(store, "ok", apps=[{"cmd": "x", "cwd": "relative"}]),
            lambda: start(store, "ok", apps=[{"cwd": "/"}]),
            lambda: stop(store, "missing-99"),
            lambda: save(store, "missing-99"),
            lambda: restore(store, "missing-99"),
            lambda: stop(store, "no-dash-id"),
        ):
            try:
                bad_call()
            except SessionError:
                pass
            else:
                raise AssertionError("expected SessionError")
        # CLI smoke through main()
        assert main(["--store", store, "start", "cli", "--app", "top"]) == 0
        assert main(["--store", store, "list"]) == 0
        assert main(["--store", store, "stop", "cli-01"]) == 0
        assert main(["--store", store, "save", "cli-01"]) == 0
        assert main(["--store", store, "restore", "cli-01"]) == 0
        assert main(["--store", store, "restore", "ghost-01"]) == 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
