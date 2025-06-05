# OFFICIAL AWS LAMBDA BASE IMAGE FOR PYTHON 3.10
FROM public.ecr.aws/lambda/python:3.10

# SET ENVIRONMENT VARIABLE
ENV PIP_NO_CACHE_DIR=1

# SET WORKING DIRECTORY
WORKDIR /var/task

# INSTALL REQUIRED SYSTEM-LEVEL PACKAGES FOR:
# - librosa
# - opencv-headless
# - tensorflow
RUN yum install -y \
    libGL \
    glib2 \
    libsndfile \
    ffmpeg \
    && yum clean all

# COPY REQUIREMENTS FILE AND INSTALL PYTHON DEPENDENCIES
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# COPY APPLICATION CODE
COPY . .

# SET THE HANDLER
CMD ["tagging.lambda_handler"]
