from lan_roster.bootstrap import bootstrap


def main():
    app = bootstrap()
    print("[*] Starting LANRoster on http://0.0.0.0:8000")
    app.run(host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
