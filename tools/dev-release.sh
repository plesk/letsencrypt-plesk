#!/bin/sh -xe
# Release dev packages to PyPI

version="0.0.0.dev$(date +%Y%m%d)"
DEV_RELEASE_BRANCH="dev-release"
RELEASE_GPG_KEY="${RELEASE_GPG_KEY:-9B3AF83D}"

# port for a local Python Package Index (used in testing)
PORT=${PORT:-1234}

tag="v$version"
mv "dist.$version" "dist.$version.$(date +%s).bak" || true
git tag --delete "$tag" || true

tmpvenv=$(mktemp -d)
virtualenv --no-site-packages $tmpvenv
. $tmpvenv/bin/activate
# update setuptools/pip just like in other places in the repo
pip install -U setuptools
pip install -U pip  # latest pip => no --pre for dev releases
pip install -U wheel  # setup.py bdist_wheel

# newer versions of virtualenv inherit setuptools/pip/wheel versions
# from current env when creating a child env
pip install -U virtualenv

root="$(mktemp -d -t le.$version.XXX)"
echo "Cloning into fresh copy at $root"  # clean repo = no artificats
git clone . $root
git rev-parse HEAD
cd $root
git branch -f "$DEV_RELEASE_BRANCH"
git checkout "$DEV_RELEASE_BRANCH"

sed -i "s/^__version.*/__version__ = '$version'/" letsencrypt_plesk/__init__.py

git add -p  # interactive user input
git commit --gpg-sign="$RELEASE_GPG_KEY" -m "Release $version"
git tag --local-user "$RELEASE_GPG_KEY" \
    --sign --message "Release $version" "$tag"

echo "Preparing sdists and wheels"
python setup.py clean
rm -rf build dist
python setup.py sdist
python setup.py bdist_wheel

echo "Signing"
for x in dist/*.tar.gz dist/*.whl
do
    gpg2 --detach-sign --armor --sign $x
done

mkdir "dist.$version"
mv dist "dist.$version/letsencrypt-plesk"

echo "Testing packages"
cd "dist.$version"
# start local PyPI
python -m SimpleHTTPServer $PORT &
local_pypi_pid=$!
echo "Local PyPI PID $local_pypi_pid"
# cd .. is NOT done on purpose: we make sure that all subpackages are
# installed from local PyPI rather than current directory (repo root)
virtualenv --no-site-packages ../venv
. ../venv/bin/activate
pip install -U setuptools
pip install -U pip
# Now, use our local PyPI
pip install \
  --extra-index-url https://testpypi.python.org/pypi \
  --extra-index-url http://localhost:$PORT \
  letsencrypt-plesk
# stop local PyPI
kill $local_pypi_pid

# freeze before installing anything else, so that we know end-user KGS
# make sure "twine upload" doesn't catch "kgs"
mkdir ../kgs
kgs="../kgs/$version"
pip freeze | tee $kgs
pip install nose
nosetests letsencrypt_plesk

echo "New root: $root"
echo "KGS is at $root/kgs"
echo "In order to upload packages run the following command:"
echo twine upload "$root/dist.$version/*/*"
echo "git remote remove tmp || true"
echo "git remote add tmp $root"
echo "git fetch tmp"
echo "git push origin v$version"
