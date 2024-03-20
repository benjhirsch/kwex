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
		// some comments
		// more comments
        String jsonValFile = args[0];
        String tmpFilePath = args[1];
        String tmpFileName = args[2];
        String outFileName = args[3];

        try {
            ObjectMapper objMpr = new ObjectMapper();
            JsonNode rootNode = objMpr.readTree(new File(jsonValFile));
            Map<String, Object> valMap = jsonToMap(rootNode);

            VelocityEngine velEng = new VelocityEngine();
            velEng.setProperty(RuntimeConstants.RESOURCE_LOADER, "file");
            velEng.setProperty("file.resource.loader.path", tmpFilePath);
            velEng.init();

            VelocityContext context = new VelocityContext();
            context.put("numberTool", new NumberTool());

            for (String key : valMap.keySet()) {
                context.put(key, valMap.get(key));
            }

            Template tmp = null;
            tmp = velEng.getTemplate(tmpFileName);

            StringWriter strWriter = new StringWriter();
            tmp.merge(context, strWriter);
            String output = strWriter.toString();

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
        Map<String, Object> resMap = new HashMap<>();

        Iterator<Map.Entry<String, JsonNode>> fields = node.fields();
        while (fields.hasNext()) {
            Map.Entry<String, JsonNode> entry = fields.next();
            if (entry.getValue().isValueNode()) {
                if (entry.getValue().isTextual()) {
                    resMap.put(entry.getKey(), entry.getValue().textValue().replaceAll("\\\"", ""));
                }
                else {
                    resMap.put(entry.getKey(), entry.getValue());
                }
            }
            else if (entry.getValue().isArray()) {
                List<Object> arrList = new ArrayList<>();
                for (JsonNode element : entry.getValue()) {
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
            else {
                resMap.put(entry.getKey(), jsonToMap(entry.getValue()));
            }
        }
        return resMap;
    }
}
