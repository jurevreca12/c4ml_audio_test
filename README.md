# c4ml\_audio\_tests
Run the following commands to recreate the results.
```
	python -m venv vevn
	source venv/bin/activate
	cd chisel4ml
	pip install -ve .[dev]
	cd ..
	python train.py
	make all
```
