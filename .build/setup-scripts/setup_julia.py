#!/usr/bin/env python3
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

# Requirements:
# - Run as the root user
# - The JULIA_PKGDIR environment variable is set

import os
import platform
import shutil
import subprocess
from pathlib import Path

import requests


def unify_aarch64(platform: str) -> str:
    """
    Renames arm64->aarch64 to support local builds on on aarch64 Macs
    """
    return {
        "aarch64": "aarch64",
        "arm64": "aarch64",
        "x86_64": "x86_64",
    }[platform]


def get_latest_julia_url() -> tuple[str, str]:
    """
    Get the last stable version of Julia
    Based on: https://github.com/JuliaLang/www.julialang.org/issues/878#issuecomment-749234813
    """

    versions = requests.get(
        "https://julialang-s3.julialang.org/bin/versions.json"
    ).json()
    stable_versions = {k: v for k, v in versions.items() if v["stable"]}
    latest_version_files = stable_versions[max(stable_versions)]["files"]
    triplet = unify_aarch64(platform.machine()) + "-linux-gnu"
    file_info = [vf for vf in latest_version_files if vf["triplet"] == triplet][0]
    return file_info["url"], file_info["version"]


def download_julia(julia_url: str) -> None:
    """
    Downloads and unpacks julia
    The resulting julia directory is "/opt/julia-VERSION/"
    """
    tmp_file = Path("/tmp/julia.tar.gz")
    subprocess.check_call(
        ["curl", "--progress-bar", "--location", "--output", tmp_file, julia_url]
    )
    # shutil.unpack_archive(tmp_file, "/opt/")
    # tmp_file.unlink()


# def prepare_julia(julia_version: str) -> None:
#     """
#     Creates /usr/local/bin/julia symlink
#     Make Julia aware of conda libraries
#     Creates a directory for Julia user libraries
#     """
#     # Link Julia installed version to /usr/local/bin, so julia launches it
#     subprocess.check_call(
#         ["ln", "-fs", f"/opt/julia-{julia_version}/bin/julia", "/usr/local/bin/julia"]
#     )

#     # Tell Julia where conda libraries are
#     Path("/etc/julia").mkdir()
#     Path("/etc/julia/juliarc.jl").write_text(
#         f'push!(Libdl.DL_LOAD_PATH, "{os.environ["CONDA_DIR"]}/lib")\n'
#     )

#     # Create JULIA_PKGDIR, where user libraries are installed
#     JULIA_PKGDIR = Path(os.environ["JULIA_PKGDIR"])
#     JULIA_PKGDIR.mkdir()
#     subprocess.check_call(["chown", os.environ["NB_USER"], JULIA_PKGDIR])
#     subprocess.check_call(["fix-permissions", JULIA_PKGDIR])

def prepare_julia(julia_version: str,conda_env_name: str, jupyter_env_name: str) -> None:
    """
    Prepares Julia for use with a specific Conda environment.
    
    :param julia_version: The version of Julia to be prepared.
    :param conda_env_name: The name of the Conda environment.
    """
    conda_env_path = os.path.join(os.environ["CONDA_DIR"], "envs", conda_env_name)

    # Create a directory for Julia within the Conda environment
    julia_env_path = os.path.join(conda_env_path, "julia")
    # os.makedirs(julia_env_path, exist_ok=True)

    # Unpack Julia into this directory
    julia_tar_path = f"/tmp/julia.tar.gz"
    shutil.unpack_archive(julia_tar_path, conda_env_path,"gztar")
    os.remove(julia_tar_path)
    
    subprocess.check_call(
        ["mv", os.path.join(conda_env_path, f"julia-{julia_version}"), julia_env_path]
    )
    
    # # List all files and directories in conda_env_path
    # print(f"Contents of {julia_env_path} after unpacking:")
    # for root, dirs, files in os.walk(julia_env_path):
    #     for name in files:
    #         print(os.path.join(root, name))
    #     for name in dirs:
    #         print(os.path.join(root, name))
    
    # Link Julia binary to a location in the PATH
    julia_bin_path = os.path.join(julia_env_path, "bin", "julia")
    os.makedirs(os.path.join(conda_env_path, "bin"), exist_ok=True)
    symlink_path = os.path.join(conda_env_path, "bin", "julia")
    if os.path.exists(symlink_path):
        os.remove(symlink_path)
    os.symlink(julia_bin_path, symlink_path)

     # Symlink Julia binary to the Jupyter environment
    jupyter_env_bin_path = os.path.join(os.environ["CONDA_DIR"], "envs", jupyter_env_name, "bin")
    os.makedirs(jupyter_env_bin_path, exist_ok=True)
    jupyter_symlink_path = os.path.join(jupyter_env_bin_path, "julia")

    if os.path.exists(jupyter_symlink_path):
        os.remove(jupyter_symlink_path)
    
    os.symlink(julia_bin_path, jupyter_symlink_path)
    
    # Set up Julia environment variables
    # julia_pkg_dir = os.path.join(julia_env_path, "packages")
    julia_pkg_dir = os.environ["JULIA_PKGDIR"]
    os.makedirs(julia_pkg_dir, exist_ok=True)
    # os.environ["JULIA_DEPOT_PATH"] = julia_pkg_dir
    # os.environ["JULIA_PKGDIR"] = julia_pkg_dir  # if still needed

    # Additional configurations can be added here if required
    # Create and configure juliarc.jl within the Julia environment
    julia_startup_dir = os.path.join(julia_env_path, "etc", "julia")
    os.makedirs(julia_startup_dir, exist_ok=True)
    julia_startup_file = os.path.join(julia_startup_dir, "juliarc.jl")

    with open(julia_startup_file, 'w') as f:
        f.write(f'push!(Libdl.DL_LOAD_PATH, "{os.path.join(conda_env_path, "lib")}")\n')

if __name__ == "__main__":
    julia_url, julia_version = get_latest_julia_url()
    download_julia(julia_url=julia_url)
    prepare_julia(julia_version=julia_version,conda_env_name='julia-env',jupyter_env_name='jupyter')
