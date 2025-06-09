# Lambda base image with Python 3.10
FROM public.ecr.aws/lambda/python:3.10

# Avoid cache bloat
ENV PIP_NO_CACHE_DIR=1

# Set the Numba cache directory to /tmp, which is writable in Lambda
ENV NUMBA_CACHE_DIR /tmp

# Working directory
WORKDIR /var/task

# Required for librosa + soundfile
RUN yum install -y libsndfile ffmpeg && yum clean all

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy rest of the app (wrapper, models, etc.)
COPY . .

# Lambda handler entry
CMD ["audio_query_tagging.lambda_handler"]