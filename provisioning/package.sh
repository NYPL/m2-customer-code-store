# Build dependencies:
pip install -r requirements.txt --target ./build
pip install "psycopg[binary,pool]"

# Move required application files into build:
cp *.py build/.
cp -R config build/.

cd build/
zip -qr build.zip *