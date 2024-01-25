# c4ml\_audio\_tests
Run the following commands to recreate the results.
```
	python -m venv vevn
	source venv/bin/activate
	cd chisel4ml
	pip install -ve .[dev]
	java -jar chisel4ml/bin/chisel4ml.jar -d /tmp/.chisel4ml0/ -p 50000
	java -jar chisel4ml/bin/chisel4ml.jar -d /tmp/.chisel4ml1/ -p 50001
	java -jar chisel4ml/bin/chisel4ml.jar -d /tmp/.chisel4ml2/ -p 50002
	java -jar chisel4ml/bin/chisel4ml.jar -d /tmp/.chisel4ml3/ -p 50003
	cd ..
	source $XILINX_PATH/Vivado/2022.2/settings.sh
	python run_tests.py
	python visualize.py
```
