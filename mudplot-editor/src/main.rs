use std::env;
use std::net::SocketAddr;

const USAGE: &str = "mudplot-editor [--bind LOOPBACK:PORT] [--python PATH]";

fn parse_args(args: impl IntoIterator<Item = String>) -> Result<Option<(String, String)>, String> {
    let mut bind = env::var("MUDPLOT_BIND").unwrap_or_else(|_| "127.0.0.1:8766".into());
    let mut python = env::var("MUDPLOT_PYTHON").unwrap_or_else(|_| "python3".into());
    let mut args = args.into_iter();
    while let Some(flag) = args.next() {
        match flag.as_str() {
            "-h" | "--help" => return Ok(None),
            "--bind" => {
                bind = args
                    .next()
                    .ok_or_else(|| "--bind requires a value".to_owned())?;
            }
            "--python" => {
                python = args
                    .next()
                    .ok_or_else(|| "--python requires a value".to_owned())?;
            }
            _ => return Err(format!("unknown argument {flag:?}")),
        }
    }
    Ok(Some((bind, python)))
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let Some((bind, python)) = parse_args(env::args().skip(1))? else {
        println!("{USAGE}");
        return Ok(());
    };
    let addr: SocketAddr = bind.parse()?;
    mudplot_editor::serve(addr, python).await
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn help_and_unknown_flags_do_not_consume_phantom_values() {
        assert!(parse_args(["--help".into()]).unwrap().is_none());
        assert_eq!(
            parse_args(["--unknown".into()]).unwrap_err(),
            "unknown argument \"--unknown\""
        );
        assert_eq!(
            parse_args(["--bind".into()]).unwrap_err(),
            "--bind requires a value"
        );
    }
}
