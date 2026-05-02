# Sanitizing Storage Adapter
# ==========================
# Guard Door component responsible for safe file storage.
#
# Security Requirements addressed:
#   - SR-10  : Sanitize and constrain all uploaded file storage paths
#   - SR-10a : Sanitize uploaded filenames to remove path traversal sequences
#   - SR-10b : Constrain all file storage paths to the designated storage root
#
# Architectural Decision:
#   - AD-03b : Implement Sanitizing Storage Adapter
#              (filename normalisation and path confinement)
#