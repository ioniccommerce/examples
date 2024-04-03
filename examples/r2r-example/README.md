# R2R Demo
[R2R](https://github.com/SciPhi-AI/R2R) RAG framework by [SciPhi](https://www.sciphi.ai/)

[Loom demonstration](https://www.loom.com/share/065eed78c0874fc988d315c0db90d7c9)

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

