import inkex, sys, copy, os, tempfile, shutil, subprocess, struct
from zipfile import ZipFile, ZIP_DEFLATED

class Svg2BlenderExport(inkex.OutputExtension):
    def __init__(self):
        inkex.Effect.__init__(self)

        init_tempdir()

    def add_arguments(self, pars):
        pars.add_argument("--dpi", type=int, default=1000)
        pars.add_argument("--front", type=str, default="front")
        pars.add_argument("--back", type=str, default="back")
        pars.add_argument("--cuts", type=str, default="cuts")

    def save(self, stream):
        layers = get_layers(self.document)
        root = self.document.getroot()

        layer_id_map = {
            self.options.front: None,
            self.options.back: None,
            self.options.cuts: None,
        }

        for layer in layers:
            layer_name_attrib = "{%s}label" % layer.nsmap["inkscape"]
            if layer_name_attrib in layer.attrib:
                layer_name = layer.attrib[layer_name_attrib]

                for name in layer_id_map:
                    if name == layer_name:
                        layer_id_map[name] = layer.attrib["id"]

        abort = False
        for key, value in layer_id_map.items():
            if value == None:
                abort = True
                inkex.utils.errormsg("error: failed to find layer \"%s\"" % key)
        if abort:
            self.abort(stream)

        front_layer_id = layer_id_map[self.options.front]
        back_layer_id = layer_id_map[self.options.back]
        cuts_layer_id = layer_id_map[self.options.cuts]

        self.layer2svg(front_layer_id)
        process1 = self.svg2png(front_layer_id)
        self.layer2svg(back_layer_id)
        process2 = self.svg2png(back_layer_id)
        self.layer2svg(cuts_layer_id)

        process1.communicate()
        process2.communicate()

        with ZipFile(stream, mode="w", compression=ZIP_DEFLATED) as file:
            file.write(get_temppath(front_layer_id, "png"), "front.png")
            file.write(get_temppath(back_layer_id, "png"), "back.png")
            file.write(get_temppath(cuts_layer_id), "cuts.svg")

            width = float(root.get("width")[:-2])
            height = float(root.get("height")[:-2])
            file.writestr("size", struct.pack("!ff", width, height))

    def layer2svg(self, layer_id):
        document = copy.deepcopy(self.document)
        root = document.getroot()

        for layer in get_layers(document):
            if layer_id == layer.attrib["id"]:
                layer.attrib["style"] = "display:inline"
            elif layer in root:
                root.remove(layer)

        document.write(get_temppath(layer_id))

    def svg2png(self, layer_id):
        svg_path = get_temppath(layer_id)
        png_path = get_temppath(layer_id, "png")
        cmd = ("inkscape", "-C", "-d", str(self.options.dpi), "-o", png_path, svg_path)
        return subprocess.Popen(cmd)

    def abort(self, stream):
        stream.close()
        os.unlink(stream.name)
        
        raise inkex.AbortExtension()

def get_layers(doc):
    return doc.xpath("//svg:g[@inkscape:groupmode=\"layer\"]", namespaces=inkex.NSS)

def get_tempdir():
    return os.path.join(tempfile.gettempdir(), "svg2blender_tmp")

def get_temppath(filename, extension="svg"):
    return os.path.join(get_tempdir(), filename + "." + extension)

def init_tempdir():
    tempdir = get_tempdir()
    if os.path.exists(tempdir):
        shutil.rmtree(tempdir)
    os.makedirs(tempdir)

if __name__ == "__main__":
    # hacky way to fix file ext not being present in output path all the time
    for i, arg in enumerate(sys.argv):
        if arg.startswith("--output=") and not arg.endswith(".fpnl"):
            sys.argv[i] = arg + ".fpnl"
    
    Svg2BlenderExport().run()
