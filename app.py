from lan_roster.bootstrap import bootstrap

# Root-level entry point maintaining backward compatibility
if __name__ == "__main__":
    from lan_roster.__main__ import main

    main()
else:
    app = bootstrap()
