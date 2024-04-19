FROM python:3.10.12
RUN pip install ipython==8.23.0
RUN pip install ipdb==0.13.13
RUN useradd -u 1000 docker_user
RUN mkdir -p /home/docker_user/app/
RUN chown -R docker_user:docker_user /home/docker_user
USER docker_user

