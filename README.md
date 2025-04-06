# Lucas_ting
For at køre skal du:
- Sætte et virtual environment (```venv```) op. God praksis er at placere det i repository.
    - Åbn ```Powershell```på dit windows monster og naviger til mappen:
        ```sh
        cd stien\til\mappen\Lucas_ting
        ```
    - Lav et Python 3.10 ```venv```:
        ```sh
        python3.10 -m venv navn_paa_dit_venv
        ```
        N.B. hvis du får en error med at python3.10 ikke eksisterer skal du sørge for at det er installeret på dit windows monster og at python 3.10 alias er udstillet i din powershells ```PATH```. Det gør du ved:
        - [Download Python 3.10](https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe)
        - Installer det ved at køre .exe-filen du lige har hentet og sørg for at markere fluebenet "Add Python 3.10 to PATH" under installationen.
        - Genstart powershell og test at den genkender python3.10 alias ved at:
                ```sh
                python3.10 --version
                ```
    - Aktivér 'navn_paa_dit_venv' ```venv```:
        ```sh
        .\navn_paa_dit_venv\Scripts\Activate.ps1
        ```
    - Installer Python afhængigheder defineret i [requirements.txt](requirements.txt):
        ```sh
        pip install -r requirements.txt
        ```
- Du burde nu kunne køre scriptet. Åben din powershell, naviger til det her repo, aktiver dit ```venv```og prøv så at køre:
    ```sh
    python -m light_analyzer.app
    ```
