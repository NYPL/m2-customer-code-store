.DEFAULT: help

help:
	@echo "make help"
	@echo "    display this help statement"
	@echo "make test"
	@echo "    run associated test suite with pytest"

test: 
				pytest