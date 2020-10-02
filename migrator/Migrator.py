import logging
import copy
from threading import Thread
from Queue import Queue

class Migrator(object):
    def __init__(self, source_registry, artifactory_access, work_queue, workers, overwrite, dir_path, source_project, target_subfolder):
        self.log = logging.getLogger(__name__)
        self.source = source_registry
        self.target = artifactory_access
        self.work_queue = work_queue
        self.failure_queue = Queue()
        self.skipped_queue = Queue()
        self.overwrite = overwrite
        self.workers = workers
        self.dir_path = dir_path
        self.source_project = source_project
        self.target_subfolder = target_subfolder
    '''
        Iterates over the Queue until all images have been uploaded (or have failed to upload)
    '''
    def migrate(self):
        for i in range(self.workers):
            t = Thread(target=self.__worker, args=(i,))
            t.daemon = True
            t.start()
        self.work_queue.join()

    '''
        Consumes image/tags that need to be uploaded from Queue until Queue is empty
        Builds shared list of failed entries
        @param idx - The index (or ID) of this worker. Should be unique across all concurrent workers.
    '''
    def __worker(self, idx):
        # The endpoint resources are not thread safe, make deep copies
        source = copy.deepcopy(self.source)
        target = copy.deepcopy(self.target)
        while True:
            image, tag = self.work_queue.get()
            target_image = image
            if (self.source_project != ""):
                if (self.target_subfolder == ""):
                    target_image = target_image.replace(self.source_project+"/", "", 1)
                else:
                    target_image = target_image.replace(self.source_project, self.target_subfolder, 1)
                print("changed target_image is: %s\n" %target_image)

            failure = True
            try:
                if self.overwrite or not target.image_exists(target_image, tag):
                    failure = not self.__upload_image(source, target, image, target_image, tag, idx)
                else:  # Image already exists and we should not overwrite it
                    failure = False
                    self.skipped_queue.put((image, tag))
            except Exception as ex:
                self.log.error("Upload of %s/%s failed." % (image, tag))
            if failure:
                self.failure_queue.put((image, tag))
            self.work_queue.task_done()

    '''
        Attempts to upload the specified image from the source to the target
        @source - The source registry
        @target - The target Artifactory instance
        @image - The image name
        @tag - The tag name
    '''
    def __upload_image(self, source, target, image, target_image, tag, idx):
        self.log.info("Uploading image %s/%s..." % (image, tag))
        layer_file = "%s/layer%d.out" % (self.dir_path, idx)
        manifest_file = "%s/manifest%d.json" % (self.dir_path, idx)
        # Get the manifest
        if source.download_manifest(image, tag, manifest_file):
            # Read in all the layers and try to deploy them
            type, layers = source.interpret_manifest(manifest_file)
            for layer in layers:
                sha2 = layer.replace('sha256:', '')
                # Try to perform a sha2 checksum deploy to avoid downloading the layer from source
                if not target.checksum_deploy_sha2(target_image, tag, sha2):
                    # Sha2 checksum failed, download the file
                    sha1 = source.download_layer(image, layer, layer_file)
                    if sha1:
                        # Try a sha1 checksum deploy to avoid upload to target
                        if not target.checksum_deploy_sha1(target_image, tag, sha2, sha1):
                            # All checksum deploys failed, perform an actual upload
                            if not target.upload_layer(target_image, tag, sha2, layer_file):
                                self.log.error("Unable to upload layer %s for %s/%s" % (layer, target_image, tag))
                                return False
                    else:
                        self.log.error("Unable to get layer %s for %s/%s..." % (layer, image, tag))
                        return False
            # Finished uploading all layers, upload the manifest
            if not target.upload_manifest(target_image, tag, type, manifest_file):
                self.log.error("Unable to deploy manifest for %s/%s..." % (image, tag))
                return False
            return True
        else:
            self.log.error("Unable to get manifest for %s/%s..." % (image, tag))
            return False

    def get_failure_queue(self):
        return self.failure_queue

    def get_skipped_queue(self):
        return self.skipped_queue







