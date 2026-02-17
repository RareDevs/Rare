import platform

if platform.system() == "FreeBSD":
    from .subreaper_bsd import subreaper
elif platform.system() == "Linux":
    from .subreaper_linux import subreaper
else:
    raise RuntimeError(f"Unsupported subrepaer platform {platform.system()}")

__all__ = ["subreaper"]
