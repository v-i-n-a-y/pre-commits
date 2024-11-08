# Handy git pre commits


Starting this as a nice way to keep my pre commits easy to find rather than combing through old repositories...laziness to be honest

## How to use

- Copy script to .git/hooks/pre-commit
- chmod +x the file


## Formatters

- python-black
   - Runs black on files about to be commited
 
- python-ruff
  - Runs riff on the files about to be commited
  - Remember to define your rules
  - Personal preference for larger python projects

- sh-beautysh
  - Formats sh scripts
	- Need to have beautysh installed via pip though
	- Not ideal but formatted code is easier on the eyes


