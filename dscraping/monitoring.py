import inspect
import typer


def echo(message: str = "", bold: bool = False):
    typer.echo(typer.style(message, fg=typer.colors.GREEN, bold=bold))


def echo_error(message: str):
    typer.echo(typer.style(message, fg=typer.colors.RED, bold=True))


def echo_warning(message: str):
    typer.echo(typer.style(message, fg=typer.colors.YELLOW, bold=True))


def monitor(active: bool = True):
    """
    Return a decorator that print the info of the target function when is called.
    """

    def decorator(func):
        def wrapper(*args):
            args_names = inspect.getfullargspec(func)[0][1:]
            args_values = args[1:]
            args_str = ", ".join(
                f"{name}={value}" for name, value in zip(args_names, args_values)
            )
            s = f"{args[0]} call => {func.__name__} ({args_str})"
            echo(s)
            try:
                result = func(*args)
            except Exception as e:
                raise e
            return result

        return wrapper if active else func

    return decorator
