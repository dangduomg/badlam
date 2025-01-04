# badlam


Badlam is a lambda calculus implementation made by basically stealing code from
[baba-lang](https://github.com/dangduomg/baba-lang), which already has
infrastructure for lambda functions, then removing the redundant parts, which
is why Badlam code is so bloated and riddled with things very unnecessary for
lambda calculus (such as `Class`, `Instance`, `BLError`, etc). Don't judge it.


## How to install and use Badlam

Installing and running Badlam is simple:
1. Prerequisites: Python 3 (At least 3.12 can be sure to work),
Lark (see requirements.txt).
2. Either:
* Download the latest point release on GitHub (recommended, as it is stable)
* Clone the repository
```sh
git clone https://github.com/dangduomg/badlam.git
```
3. Set working directory to the project root.
```sh
cd badlam
```
4. (Optionally) Create and activate a virtual environment.
```sh
python3 -m venv .venv
source .venv/bin/activate
```
5. Install requirements.
```sh
pip install -r requirements.txt
```
6. Run `src/main.py` without arguments to open an interactive prompt. To run
a source file, enter `src/main.py <file>`. Source files are of extension
`.blm`. Run `src/main.py -h` for further help.