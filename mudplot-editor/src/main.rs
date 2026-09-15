use std::env;
use std::net::SocketAddr;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut bind = env::var("MUDPLOT_BIND").unwrap_or_else(|_| "127.0.0.1:8766".into());
    let mut python = env::var("MUDPLOT_PYTHON").unwrap_or_else(|_| "python3".into());
    let mut args = env::args().skip(1);
    while let Some(flag) = args.next() {
        let value = args
            .next()
            .ok_or_else(|| format!("{flag} requires a value"))?;
        match flag.as_str() {
            "--bind" => bind = value,
            "--python" => python = value,
            _ => return Err(format!("unknown argument {flag:?}").into()),
        }
    }
    let addr: SocketAddr = bind.parse()?;
    mudplot_editor::serve(addr, python).await
}
