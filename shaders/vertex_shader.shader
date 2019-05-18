# version 460

layout (location = 0) in vec4 position;
layout (location = 1) in vec4 normal;
layout (location = 2) in vec2 texcoords;

uniform mat4 model_matrix;
uniform mat4 view_matrix;
uniform mat4 projection_matrix;
uniform vec4 color;
uniform vec4 shader_light;

out vec4 vertexColor;
out vec2 vertexTexcoords;

void main() 
{
    float intensity = dot(normal, normalize(shader_light - position));
    gl_Position = projection_matrix * view_matrix * model_matrix * position;
    vertexColor = color * intensity;
    vertexTexcoords = texcoords;
}