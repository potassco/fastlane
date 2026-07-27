# Program

Below is the program to use this LNS framework with the [potassco-benchmark-tool].
Create an executable file with the name `mod_lns-conda` and contents below inside the
`programs` folder created by `btool init`.

```
#!/bin/bash

# Load environment modules for your application here.
# Only required for seq jobs, for dist jobs see single.dist template.
#source ~/.bashrc
#source ~/miniconda3/bin/activate
#source activate lns

exec mod_lns "${@}" 2> solver.err
```

[potassco-benchmark-tool]: https://potassco.org/benchmark-tool/
