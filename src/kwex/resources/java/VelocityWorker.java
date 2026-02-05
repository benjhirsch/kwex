import java.io.*;
import java.util.*;
import com.fasterxml.jackson.databind.*;
import org.apache.velocity.VelocityContext;
import org.apache.velocity.app.VelocityEngine;
import org.apache.velocity.runtime.RuntimeConstants;
import org.apache.velocity.Template;
import org.apache.velocity.tools.generic.NumberTool;

public class VelocityWorker {

    private static final ObjectMapper MAPPER = new ObjectMapper();
    public static void main(String [] args) throws Exception {
        BufferedReader in = new BufferedReader(new InputStreamReader(System.in));
        BufferedWriter out = new BufferedWriter(new OutputStreamWriter(System.out));

        String templatePath = args[0];
        String templateName = args[1];

        VelocityEngine velEng = new VelocityEngine();
        velEng.setProperty(RuntimeConstants.RESOURCE_LOADER, "file");
        velEng.setProperty("file.resource.loader.path", templatePath);
        velEng.init();

        Template tmp = null;
        tmp = velEng.getTemplate(templateName);

        String line;
        while ((line = in.readLine()) != null) {
            try {
                Map<String, Object> req = MAPPER.readValue(line, Map.class);
                if ("terminate".equals(req.get("cmd"))) {
                    break;
                }
                
                String outputFileName = (String) req.get("output_file_name");

                JsonNode rootNode = MAPPER.readTree(line);
                Map<String, Object> valMap = jsonToMap(rootNode);

                VelocityContext context = new VelocityContext();
                context.put("numberTool", new NumberTool());
                for (String key : valMap.keySet()) {
                    context.put(key, valMap.get(key));
                }

                StringWriter strWriter = new StringWriter();
                tmp.merge(context, strWriter);
                String output = strWriter.toString();

                try (BufferedWriter writer = new BufferedWriter(new FileWriter(outputFileName))) {
                    writer.write(output);
                } catch (IOException e) {
                    e.printStackTrace();
                }

                out.write("ok\n");
                out.flush();
            } catch (Exception e) {
                out.write(e.getMessage() + "\n");
                out.flush();
            }
        }

        return;
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