# 😈 Demonstration Support

The files here support the demonstration deployment of the "renaissance" EDRN portal, typically available at https://edrn.jpl.nasa.gov/renaissance.

The scripts are:

- `deploy.sh`. This is run nightly on `edrn-docker` to pull the Docker image for the portal and start the Docker composition.
- `static-media-xfer.sh`. This is run nightly on `cancer` to make static files and media files available on the web server that handles `edrn.jpl.nasa.gov`, which is not `edrn-docker`, but `cancer`.
