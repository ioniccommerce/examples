# R2R Demo
[R2R](https://github.com/SciPhi-AI/R2R) RAG framework by [SciPhi](https://www.sciphi.ai/)

Simple example of RAG-based product search.

Update query term in client.py.

```
pip install 'r2r[parsing,eval]'
pip install IONIC-API-SDK

export OPENAI_API_KEY=sk-...
export LOCAL_DB_PATH=local.sqlite

python -m main # run server
python -m client # run client

```

