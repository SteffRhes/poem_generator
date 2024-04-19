FROM python:3.10.12
RUN useradd -u 1000 docker_user
RUN mkdir -p /home/docker_user/app/
RUN chown -R docker_user:docker_user /home/docker_user
USER docker_user

