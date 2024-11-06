FROM debian:latest
ARG GITHUB_TOKEN

ENV GITHUB_TOKEN=${GITHUB_TOKEN}
ENV GH_TOKEN=${GITHUB_TOKEN}

RUN apt-get update && apt-get install -y bash curl git gpg

RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | gpg --dearmor -o /usr/share/keyrings/githubcli-archive-keyring.gpg;

RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null;

RUN apt update && apt install -y gh;

RUN gh extension install https://github.com/nektos/gh-act

RUN mkdir /app
VOLUME /app
WORKDIR /app
