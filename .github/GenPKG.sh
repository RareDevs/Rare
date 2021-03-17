export PYTHONPATH=$PWD
version=$(python3 Rare --version)
cd .github
git clone https://aur.archlinux.org/rare.git
cd ..
sed -i "s/.*pkgver=.*/pkgver=$version/" .github/rare/PKGBUILD
