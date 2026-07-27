# Runscripts

Below you can find two runscripts to use this LNS framework with the [potassco-benchmark-tool].
Create a xml file with the contents below inside the `runscripts` folder created by `btool init`.
Use `runscript-seq-lns.xml` for local benchmarks and `runscript-dist-lns.xml` for benchmarks on the cluster.

`runscript-seq-lns.xml`:

```
<runscript output="lns-output">

	<machine name="houat" cpu="8xE5520@2.27GHz" memory="24GB"/>

  	<config name="seq-generic" template="templates/seq-generic.sh"/>

	<system name="mod_lns" version="conda" measures="clasp" config="seq-generic">
    		<setting name="classic_lns" cmdline="--preset=lns" tag="basic">
				<variable cmd="--destruction=simple,{}" value="40;60"/>
			</setting>
			<setting name="alnps" cmdline="--preset=alnps" tag="basic">
				<encoding file="./configs/sgp/random_N.lp"/>
			</setting>
	</system>

	<seqjob name="seq-lns" timeout="1800" runs="2" parallel="1"/>

	<benchmark name="lns">
		<folder path="./benchmarks/sgp"/>
	</benchmark>

	<project name="lns-seq-job" job="seq-lns">
		<runtag machine="houat" benchmark="lns" tag="basic"/>
	</project>

</runscript>
```

`runscript-dist-lns.xml`:
```
<runscript output="lns-output">

	<machine name="houat" cpu="8xE5520@2.27GHz" memory="24GB"/>

  	<config name="dist-generic" template="templates/seq-generic.sh"/>

	<system name="mod_lns" version="conda" measures="clasp" config="dist-generic">
    		<setting name="classic_lns" cmdline="--preset=lns" tag="basic">
				<variable cmd="--destruction=simple,{}" value="40;60"/>
			</setting>
			<setting name="alnps" cmdline="--preset=alnps" tag="basic">
				<encoding file="./configs/sgp/random_N.lp"/>
			</setting>
	</system>

	<distjob name="dist-lns" timeout="1800" runs="2" template_options="--single" script_mode="timeout" walltime="1h" cpt="2"/>

	<benchmark name="lns">
		<folder path="./benchmarks/sgp"/>
	</benchmark>

	<project name="lns-dist-job" job="dist-lns">
		<runtag machine="houat" benchmark="lns" tag="basic"/>
	</project>

</runscript>

```

[potassco-benchmark-tool]: https://potassco.org/benchmark-tool/