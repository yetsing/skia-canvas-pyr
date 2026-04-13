set -eux;
apk add --no-cache --virtual .build-deps bluez-dev bzip2-dev dpkg-dev dpkg findutils gcc gdbm-dev gnupg libc-dev libffi-dev libnsl-dev libtirpc-dev linux-headers make ncurses-dev openssl-dev pax-utils readline-dev sqlite-dev tar tcl-dev tk tk-dev util-linux-dev xz xz-dev zlib-dev zstd-dev ;
wget -O python.tar.xz "https://www.python.org/ftp/python/${PYTHON_VERSION%%[a-z]*}/Python-$PYTHON_VERSION.tar.xz";
echo "$PYTHON_SHA256 *python.tar.xz" | sha256sum -c -;
mkdir -p /usr/src/python;
tar --extract --directory /usr/src/python --strip-components=1 --file python.tar.xz;
rm python.tar.xz;
cd /usr/src/python;
gnuArch="$(dpkg-architecture --query DEB_BUILD_GNU_TYPE)";
mkdir -p /opt/python/${PYTHON_VERSION};
./configure --prefix=/opt/python/${PYTHON_VERSION} --build="$gnuArch" --enable-loadable-sqlite-extensions --enable-option-checking=fatal --enable-shared $(test "${gnuArch%%-*}" != 'riscv64' && echo '--with-lto') --with-ensurepip ;
nproc="$(nproc)";
EXTRA_CFLAGS="-DTHREAD_STACK_SIZE=0x100000";
LDFLAGS="${LDFLAGS:-} -Wl,--strip-all";
arch="$(apk --print-arch)";
case "$arch" in
    x86_64|aarch64)
        EXTRA_CFLAGS="${EXTRA_CFLAGS:-} -fno-omit-frame-pointer -mno-omit-leaf-frame-pointer";
        ;;
    x86)
        ;;
    *)
        EXTRA_CFLAGS="${EXTRA_CFLAGS:-} -fno-omit-frame-pointer";
        ;;
esac;
make -j "$nproc" "EXTRA_CFLAGS=${EXTRA_CFLAGS:-}" "LDFLAGS=${LDFLAGS:-}" ;
rm python;
make -j "$nproc" "EXTRA_CFLAGS=${EXTRA_CFLAGS:-}" "LDFLAGS=${LDFLAGS:-} -Wl,-rpath='\$\$ORIGIN/../lib'" python ;
make install;
cd /;
rm -rf /usr/src/python;
find /opt/python/${PYTHON_VERSION} -depth \( \( -type d -a \( -name test -o -name tests -o -name idle_test \) \) -o \( -type f -a \( -name '*.pyc' -o -name '*.pyo' -o -name 'libpython*.a' \) \) \) -exec rm -rf '{}' + ;
find /opt/python/${PYTHON_VERSION} -type f -executable -not \( -name '*tkinter*' \) -exec scanelf --needed --nobanner --format '%n#p' '{}' ';' | tr ',' '\n' | sort -u | awk 'system("[ -e /usr/local/lib/" $1 " ]") == 0 { next } { print "so:" $1 }' | xargs -rt apk add --no-network --virtual .python-rundeps ;
apk del --no-network .build-deps;
export PYTHONDONTWRITEBYTECODE=1;
python3 --version;
pip3 --version # buildkit