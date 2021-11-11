# littlemore_ltn_analysis

Analysis and data from the Littlemore LTN questionnaire Oct 2021

- Report can be found [here](docs/report.pdf)
- The questionnaire we used can be found [here](docs/questionnaire.pdf)
- The raw data can be found [here](data)

## Running the analysis

Analysis was mainly done in Python (mostly in the notebook [`lpc_ltn_analysis.ipynb`](lpc_ltn_analysis.ipynb)), with a bit of help from [QGIS](https://qgis.org/en/site/) for making one of the maps. 

A couple of scripts used to make the supplementary data can be found under [`scripts`](scripts). 

I have only tested this code with [Python 3.9.2](https://www.python.org/downloads/). To run the notebook, create a virtual environment by doing *e.g.* 

```bash
python3 -m venv .env
source .env/bin/activate
```

Then:
```bash
python3 -m pip install -r requirements.txt
jupyter-lab lpc_ltn_analysis.ipynb
```    
