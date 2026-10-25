    # SigmaOS-session-manager

    XDG session manager (start/stop/save sessions)

    Part of the **SigmaOS** sovereign operating-system ecosystem — a multi-repository
    distribution modelled on Linux Mint and Omarchy Linux. See the parent
    [`SigmaOS`](https://github.com/AaryanSinghChauhan09/SigmaOS) repository for the
    full component index.

    ## Upstream inspirations
    - https://github.com/linuxmint/cinnamon-session

    ## Design principles applied
    - **Fail-Fast**
- **Pure Plan / Thin Execute**
- **Deterministic Testing**
- **KISS**
- **Information Hiding**

    ## Usage
    Verbs: `start, stop, save, restore, list`

    ```
    $ sigma-session --store ./sessions start browse --app firefox --app terminal
$ sigma-session --store ./sessions save browse-01
$ sigma-session --store ./sessions stop browse-01
$ sigma-session --store ./sessions restore browse-01
$ sigma-session --store ./sessions list

    ```

    ## Build & test
    ```
    make build
    make test
    ```

    ## Licence
    GNU General Public License v3.0 (FOSS).
