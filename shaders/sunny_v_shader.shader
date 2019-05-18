# version 460

layout (location = 0) in vec4 position;
layout (location = 1) in vec4 normal;
layout (location = 2) in vec2 texcoords;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform vec4 color;
uniform vec4 light;

out vec4 vertexColor;
out vec2 vertexTexcoords;

void main() 
{
    float intensity = dot(normal, normalize(light * 1000 - position));
    gl_Position = projection * view * model * position;
    vertexColor = color * intensity * 2;
    vertexTexcoords = texcoords;
}