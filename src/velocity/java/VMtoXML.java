import org.apache.velocity.VelocityContext;
import org.apache.velocity.app.VelocityEngine;
import org.apache.velocity.Template;
import org.apache.velocity.runtime.RuntimeConstants;
import org.apache.velocity.tools.generic.NumberTool;

import java.io.FileReader;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.util.Properties;

import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.StringWriter;
import java.util.Iterator;
import java.util.List;
import java.io.File;
import java.util.ArrayList;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

public class VMtoXML {
    public static void main(String[] args) {
        String jsonValFile = args[0];
        String tmpFilePath = args[1];
        String tmpFileName = args[2];
        String outFileName = args[3];

        try {
            // map json keyword value file into node structure
            ObjectMapper objMpr = new ObjectMapper();
            JsonNode rootNode = objMpr.readTree(new File(jsonValFile));
            Map<String, Object> valMap = jsonToMap(rootNode);

            // initialize velocity engine and add the .vm template to it
            VelocityEngine velEng = new VelocityEngine();
            velEng.setProperty(RuntimeConstants.RESOURCE_LOADER, "file");
            velEng.setProperty("file.resource.loader.path", tmpFilePath);
            velEng.init();

            // add NumberTool to the velocity context to enable basic in-template arithmetic
            VelocityContext context = new VelocityContext();
            context.put("numberTool", new NumberTool());

            // add all $label, $fits (plus extensions), and $spice keyword values to the Velocity context
            for (String key : valMap.keySet()) {
                context.put(key, valMap.get(key));
            }

            // get the template as a Velocity Template object
            Template tmp = null;
            tmp = velEng.getTemplate(tmpFileName);

            // merge template with context and create string representing template with pointers replaced by their values
            StringWriter strWriter = new StringWriter();
            tmp.merge(context, strWriter);
            String output = strWriter.toString();

            // write the output string to the specified output file
            try (BufferedWriter writer = new BufferedWriter(new FileWriter(outFileName))) {
                writer.write(output);
            } catch (IOException e) {
                    e.printStackTrace();
            }

        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private static Map<String, Object> jsonToMap(JsonNode node) {
        // declare a HashMap that will hold all the keyword value pairs
        Map<String, Object> resMap = new HashMap<>();

        // iterate through the fields of the JSON keyword value file, turning each one into an "entry" map
        Iterator<Map.Entry<String, JsonNode>> fields = node.fields();
        while (fields.hasNext()) {
            Map.Entry<String, JsonNode> entry = fields.next();
            // if the field entry is a simple value rather than something more complicated...
            if (entry.getValue().isValueNode()) {
                // if it's text, add the key and value to our return HashMap and remove all double quotes captured in string values
                if (entry.getValue().isTextual()) {
                    resMap.put(entry.getKey(), entry.getValue().textValue().replaceAll("\\\"", ""));
                }
                // otherwise it's probably just a number, so add that keyword and value to the hashmap
                else {
                    resMap.put(entry.getKey(), entry.getValue());
                }
            }
            // if the field entry is an array, loop through the array values
            else if (entry.getValue().isArray()) {
                List<Object> arrList = new ArrayList<>();
                for (JsonNode element : entry.getValue()) {
                    // adding them to an arraylist object which gets put into the hashmap
                    if (element.isValueNode()) {
                        if (element.isTextual()) {
                            arrList.add(element.textValue().replaceAll("\\\"", ""));
                        }
                        else {
                            arrList.add(element);
                        }
                    }
                    else {
                        arrList.add(jsonToMap(element));
                    }
                }
                resMap.put(entry.getKey(), arrList);
            }
            // if the field entry is not a simple value or array, it's a more complicated JsonNode, so send it through JsonToMap again
            else {
                resMap.put(entry.getKey(), jsonToMap(entry.getValue()));
            }
        }
        return resMap;
    }
}
