FROM python:3.10.12
RUN pip install ipython==8.23.0
RUN pip install ipdb==0.13.13
RUN pip install transformers==4.40.0
#RUN pip install tensorflow==2.16.1
RUN pip install torch==2.2.2
RUN useradd -u 1000 docker_user
RUN mkdir -p /home/docker_user/app/
RUN chown -R docker_user:docker_user /home/docker_user
USER docker_user
