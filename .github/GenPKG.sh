export PYTHONPATH=$PWD
version=$(python3 Rare --version)

sed -i "s/.*pkgver=.*/pkgver=$version/" .github/rare/PKGBUILD
