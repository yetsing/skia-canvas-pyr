FROM messense/manylinux2014-cross:x86_64

ARG LLVM_VERSION=22
ARG MATURIN_URL="https://github.com/PyO3/maturin/releases/download/v1.11.5/maturin-x86_64-unknown-linux-musl.tar.gz"

RUN apt-get update && \
  apt-get install -y --fix-missing --no-install-recommends gpg-agent ca-certificates openssl && \
  wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key | apt-key add - && \
  echo "deb http://apt.llvm.org/jammy/ llvm-toolchain-jammy-${LLVM_VERSION} main" >> /etc/apt/sources.list && \
  echo "deb-src http://apt.llvm.org/jammy/ llvm-toolchain-jammy-${LLVM_VERSION} main" >> /etc/apt/sources.list && \
  apt-get update && \
  apt-get install -y --fix-missing --no-install-recommends \
  curl \
  llvm-${LLVM_VERSION} \
  clang-${LLVM_VERSION} \
  lld-${LLVM_VERSION} \
  libc++-${LLVM_VERSION}-dev \
  libc++abi-${LLVM_VERSION}-dev \
  rcs \
  xz-utils \
  rcs \
  git \
  make \
  ninja-build && \
  ln -sf /usr/bin/clang-${LLVM_VERSION} /usr/bin/clang && \
  ln -sf /usr/bin/clang++-${LLVM_VERSION} /usr/bin/clang++ && \
  ln -sf /usr/bin/lld-${LLVM_VERSION} /usr/bin/lld && \
  curl https://sh.rustup.rs -sSf | sh -s -- -y && \
  rm -rf /var/lib/apt/lists/*

RUN echo "::group::Install maturin" && \
  curl -L ${MATURIN_URL} | tar -xz -C /usr/local/bin && \
  maturin --version

# manually build freetype & fontconfig and install fontconfig in /usr/local
COPY ./install-fontlibs.sh /opt
COPY ./freetype.cfg /opt
RUN bash /opt/install-fontlibs.sh

# move the static libs to a common location consistent across glibc & musl builds
RUN mkdir -p /opt/skia-static-libs && \
    cp /usr/local/lib/*/libfontconfig.a /opt/skia-static-libs
