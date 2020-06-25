# London Population Synthesis (LPS)

**Please note** this is the public version of a joint TfL and Arup research project (originally called mimi) to use Agent Based Modelling of transport. All sensitive data and references to data locations are removed, **including test data**. A consequence of this is that that tests will not pass.

#### MATSim Input Making Interface

Welcome to `london-population-synthesis`, a python(3) project for building activity based demand via **population 
synthesis** (agent based plans and 
attributes for [MATSim](https://matsim.org)).

#### Features

* Reading of data from a variety of sources (diaries, demand matrices, GPS traces and census 
data).
* Semi standardised abstractions for sampling and synthesising agent plans.
* Base `Population`/`Agent`/`Plan`/`Activity` & `Leg` classes for handling and combining 
populations from different sources.
* Output of `Populations` as agent plans and attributes in MATSim formatted `.xml`.
* Output of `Populations` as `.csv` information for diagnostics and assurance.

#### In more detail

Building or synthesising a representative population is a big task. Depending on the detail 
required and the data available a population might be built from multiple sources, using various 
methods of filtering, sampling and synthesis. `LPS` is intended to make this process easier, 
reusable and reproducible.

This project was originally built to support population synthesis for a London ABM. As such it originally
 supported data input from the following London-centric sources:

* **LoPopS** (London Population Synthesis): a derivative of the London (households)Travel Demand 
Survey (LTDS), ie diary data, supplied by Transport for London.
* **MoTiON** (London Demand Model): a new demand model incorporating a wide variety of population 
segmentation and complex trip tours, used to synthesise plans for agents entering London.
* **LoHAM** (London Highways Assignment Model), used to synthesise HGV and LGV freight plans.

Since, features have been added for synthesis of plans for a variety of other projects using new 
data sources and types. For example plans derived from **GPS traces** and from **census commute** data.

#### Setup

Clone and local pip install with `pip3 install -e .`.
`cd lps`
`pip3 install -r requirements.txt`
`pytest -v`  # will not work without data access

`lps -h`

```
Usage: mimi [OPTIONS] CONFIG_PATH

Options:
  -h, --help  Show this message and exit.
  ```

#### Use

`LPS` uses `.toml` configuration files. This is to aid reproducibility. You will find some 
examples in this project.

Your configuration will provide `LPS` with paths for reading input data and writing outputs to. 
S3 paths are supported and we are currently maintaining an S3 bucket with supported data sources.

#### Project Structure
.  
├── `bin`  
├── `london_synth.toml` - example config  
├── `mimi`  
│   ├── `core` - base classes and methods  
│   │   ├── `generators.py`  
│   │   ├── `matsim_maps.py`  
│   │   ├── `output.py`  
│   │   ├── `population.py`  
│   │   └── `samplers.py`  
│   ├── `motion` - project specific classes  
│   ├── `loham` - project specific classes  
│   ├── `lopops` - project specific classes  
│   ├── `momo` - project specific classes  
│   └── `factory.py`  
├── `test_data`
├── `tests`  
└── `utils`  

#### Inputs

We are using an S3 bucket for all the currently supported data sources. You will need access.
credentials.
	    
#### Outputs

* `.xml` output for MATSim Plans
* `.xml` output for MATSim Attributes
* `.csv` and terminal outputs for further visualisation and validation

#### ToDo

* Add census synthesis
* Add more Motion tour types, including non home-based tours
* Improve activity inference to deal with multi-leg trips (eg: HOME-bus->-tube->WORK-train->HOME. At the moment these are not correctly dealt with)
* Improve flexibility of generic demand inputs eg Freight & Motion
* Use OSM 'facility' data for better location sampling
* Speed up and remove some dependancies?
* Add Tourist synthesis? Random walks?
