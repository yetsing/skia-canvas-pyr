fn main() {
  // Only link libintl on musl targets (e.g., Alpine)
  if std::env::var("CARGO_CFG_TARGET_ENV").as_deref() == Ok("musl") {
    println!("cargo:rustc-link-lib=intl");
  }
}
