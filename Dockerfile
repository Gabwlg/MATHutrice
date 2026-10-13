# The image the application runs from, built once per commit and run unchanged
# in every environment. It holds the code and its locked dependencies, and no
# setting: each environment passes its own at run time.
#
#     docker build -t mathutrice .
#     docker run --env-file .env -p 8000:8000 mathutrice
#
# .env.example lists every setting the application reads.
FROM python:3.14.7-slim

# uv installs the versions in uv.lock, as it does on a contributor's machine.
COPY --from=ghcr.io/astral-sh/uv:0.12.21 /uv /bin/uv

# The base image already is the Python in .python-version, so uv must not
# download another one.
ENV UV_PYTHON_DOWNLOADS=never \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencies get a layer of their own, so a commit that changes only the code
# rebuilds only the last layers. The dev group, where tach lives, is left out.
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-dev --no-install-project

COPY mathutrice ./mathutrice
RUN uv sync --locked --no-dev

# The application writes in two places at run time: uploaded PDFs in
# mathutrice/rag_documents, and the SQLite file in the working directory.
RUN useradd --system --no-create-home app \
    && mkdir mathutrice/rag_documents \
    && chown app /app mathutrice/rag_documents
USER app

ENV PATH="/app/.venv/bin:$PATH"

# The commit the image is built from (`--build-arg REVISION=...`). The app sends
# it back in the X-Revision header, so a deploy knows which image answers. Last,
# so that it keeps the layers above it cached.
ARG REVISION=unknown
ENV REVISION=$REVISION

# The one process the old launcher started: uvicorn. The hourly cleanup job and
# the startup seed run inside it, in the app's lifespan. `exec` makes uvicorn
# the container's main process, so it receives the stop signal.
EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn mathutrice.app:app --host 0.0.0.0 --port \"${PORT:-8000}\""]
