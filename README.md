# BCI Cursor Control

Cursor control with an OpenBCI Ultracortex IV and Cyton. Heavily based on the work of Wolpaw and colleagues at the
Wadsworth Center in Albany, NY in the late 1990s and early 2000s - the "Wadsworth BCI". The primary intent of this
system is to gain confidence in the capabilities of the OpenBCI hardware and gain experience processing data from the
amplifier in real-time. Secondarily, it provides a simple and responsive system for human subject training, allowing
subjects to become comfortable with motor-imagery based BCI control.

## References

[Control of a two-dimensional movement signal by a noninvasive brain-computer interface in humans](https://www.pnas.org/content/101/51/17849/tab-article-info)

## Setup

### Conda and Pipenv

This Python code for this project utilizes both Conda and Pip to manage packages. Conda is the preferred default for 
package installation, with pip used for any Python packages hosted on PyPi. Pipenv provides a package management 
layer on top of the Pip installer, enabling dependency locking for deterministic dependency trees.

### LFS

This repository utilizes Git Large File Storage (LFS) to manage large data files containing biosensor data. You 
should download and install [Git LFS](https://git-lfs.github.com/) if you wish to access the data files.