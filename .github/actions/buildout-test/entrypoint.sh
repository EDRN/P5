#!/bin/sh -l
#
# Bootstrap, buildout, and run tests
#
# This feels … not so modular

bootstrapURL="$1"
buildoutConfig="$2"
testPackages="$3"

PATH=/usr/local/bin:/usr/bin:/bin
export PATH

mkdir $HOME/.buildout
cp /root/.buildout/default.cfg $HOME/.buildout

echo "🔍 Checking for \`bootstrap.py\` in $GITHUB_WORKSPACE…" 1>&2
cd "$GITHUB_WORKSPACE"
if [ ! -f bootstrap.py ]; then
    echo '🔍 Checking for `bootstrap-buildout.py`…' 1>&2
    if [ ! -f bootstrap-buildout.py ]; then
        echo "🚚 Retrieving a bootstrapper from $bootstrapURL" 1>&2
        curl -L "$bootstrapURL" > bootstrap.py
    else
        echo '📛 Renaming `bootstrap-buildout.py` to just `bootstrap.py`' 1>&2
        mv bootstrap-buildout.py bootstrap.py
    fi
fi

echo '🏃‍♀️ Bootstrapping the buildout and building out' 1>&2
python bootstrap.py -c "$buildoutConfig" && bin/buildout -c "$buildoutConfig"

echo '🔍 Checking for a test runner in `bin/test`' 1>&2
if [ ! -x bin/test ]; then
    echo "✋ Buildout with $buildoutConfig didn't create a test runner in bin/test; skipping tests" 1>&2
    exit 0
fi

for package in $testPackages; do
    echo "🧪 Testing $package" 1>&2
    if ! bin/test --package $package; then
        echo "🛑 Failed to run tests in $package; aborting the rest" 1>&2
        exit 1
    fi
done

echo '✋ All done' 1>&2
exit 0
