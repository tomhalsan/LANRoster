from lan_roster.bootstrap import bootstrap

# Root-level entry point maintaining backward compatibility
app = bootstrap()

if __name__ == "__main__":
    print("[*] Starting LANRoster on http://0.0.0.0:8000")
    app.run(host="0.0.0.0", port=8000)
