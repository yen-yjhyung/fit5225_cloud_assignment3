# Lambda base image with Python 3.10
FROM public.ecr.aws/lambda/python:3.10

# Working directory
WORKDIR /var/task

# Avoid cache bloat
ENV PIP_NO_CACHE_DIR=1

# Required for librosa + soundfile
RUN yum install -y libsndfile ffmpeg && yum clean all

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy rest of the app (wrapper, models, etc.)
COPY . .

# Lambda handler entry
CMD ["audio_tagging.lambda_handler"]