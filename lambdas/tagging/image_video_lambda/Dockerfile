# Lambda base image with Python 3.10
FROM public.ecr.aws/lambda/python:3.10

# Working directory
WORKDIR /var/task

# Avoid cache bloat
ENV PIP_NO_CACHE_DIR=1

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy rest of the app (wrapper, models, etc.)
COPY . .

# Lambda handler entry
CMD ["visual_tagging.lambda_handler"]