rm -rf build

# Build dependencies:
pip install -r requirements.txt --target ./build

# Move required application files into build:
cp *.py build/.
cp -R config build/.

cd build/
zip -qr build.zip *