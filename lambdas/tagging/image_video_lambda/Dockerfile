# Lambda base image with Python 3.10
FROM public.ecr.aws/lambda/python:3.10

# Avoid cache bloat
ENV PIP_NO_CACHE_DIR=1

# Working directory
WORKDIR /var/task

# # Install system-level packages for OpenCV and other dependencies
RUN yum install -y mesa-libGL libSM libXrender libXext
# RUN yum install -y \
#     libGL \
#     glib2 \
#     libsndfile \
#     ffmpeg \
#     && yum clean all

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy rest of the app (wrapper, models, etc.)
COPY . .

# Lambda handler entry
CMD ["visual_tagging.lambda_handler"]