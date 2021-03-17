export PYTHONPATH=$PWD
version=$(python3 Rare --version)
cd .github/rare
sed -i "s/.*pkgver=.*/pkgver=$version/" PKGBUILD
